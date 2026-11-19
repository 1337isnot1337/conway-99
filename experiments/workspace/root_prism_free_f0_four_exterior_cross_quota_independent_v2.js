(() => {
"use strict";
const SCHEMA="conway99.f0.four-exterior-cross-quota-independent.v1";
const KEY_HASH="2adfcc619820604a3f49463bd0fd8109113ab7ce13bceadcc49554533b09dd1c";
function insist(ok,message){if(!ok)throw Error(message);}
function bits(value){let n=0;while(value){value&=value-1;n++;}return n;}
function same(a,b,message){insist(JSON.stringify(a)===JSON.stringify(b),message);}
function cmpCase(a,b){return a[0]-b[0]||a[1]-b[1]||a[2]-b[2];}
function separateCases(masks,q,pairs,edgeIndex,n,tick){
 const tuples=[];
 for(const [i,j] of pairs){
  tick();const left=[],right=[];
  for(let v=0;v<n;v++){
   if((masks[v]&(1<<i))&&!(masks[v]&(1<<j))&&q[v][i]===1)left.push(v);
   if((masks[v]&(1<<j))&&!(masks[v]&(1<<i))&&q[v][j]===1)right.push(v);
  }
  for(const u of left)for(const v of right){
   const e=edgeIndex[u*n+v];if(e<0)continue;
   tuples.push(u<v?[e,i,j]:[e,j,i]);
   insist(tuples.length<=73404,"complete case storage bound");
  }
 }
 tuples.sort(cmpCase);
 for(let t=1;t<tuples.length;t++)insist(cmpCase(tuples[t-1],tuples[t])<0,"strict independent case order");
 return tuples;
}
function makeMixed(vertex,site,quota,edges){
 insist(Number.isInteger(vertex)&&Number.isInteger(site)&&Number.isInteger(quota),"integer mixed definition");
 const set=new Set(edges);insist(set.size===edges.length&&edges.every(Number.isInteger),"distinct exact mixed coefficients");
 return {vertex,site,quota,edges,set,index:18*vertex+site};
}
function coefficientCertificate(key,A,B){
 if(key[0]>=key[1]||new Set(key[2]).size!==key[2].length)return null;
 const selector=new Map();
 for(const M of [A,B])selector.set(M.vertex,(selector.get(M.vertex)||0)-M.quota);
 const actual=[...selector].filter(([,coefficient])=>coefficient!==0).sort((a,b)=>a[0]-b[0]);
 const required=[[key[0],-1],[key[1],-1]].sort((a,b)=>a[0]-b[0]);
 if(JSON.stringify(actual)!==JSON.stringify(required))return null;
 for(const edge of key[2]){
  const coefficient=(A.set.has(edge)?1:0)+(B.set.has(edge)?1:0);
  if(coefficient<1)return null;
 }
 const residual=A.edges.length+B.edges.length-key[2].length;
 insist(residual>=0,"nonnegative omitted mixed-edge coefficient sum");
 return residual;
}
function controls(){
 let toyCases=0,toyInstances=0,swappedCases=0;
 const h=[];for(let m=1;m<16;m++)h.push([0,1,2,3].filter(i=>m&(1<<i)));
 const masks=h.map(s=>s.reduce((v,i)=>v|(1<<i),0)),pairs=[];
 for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)pairs.push([i,j]);
 for(let seed=0;seed<16;seed++){
  const n=h.length,q=h.map((_,v)=>[0,1,2,3].map(i=>seed===0?1:(seed+v+2*i)%3)),edges=[],index=new Int32Array(n*n).fill(-1);
  for(let a=0;a<n;a++)for(let b=a+1;b<n;b++){
   if(bits(masks[a]&masks[b])>1||!h[b].every(i=>q[a][i]>0)||!h[a].every(i=>q[b][i]>0))continue;
   index[a*n+b]=index[b*n+a]=edges.length;edges.push([a,b]);
  }
  const got=separateCases(masks,q,pairs,index,n,()=>{}),wanted=[];
  for(let e=0;e<edges.length;e++){
   const [b,c]=edges[e];
   for(const i of h[b])for(const j of h[c])
    if(!(masks[b]&(1<<j))&&!(masks[c]&(1<<i))&&q[b][i]===1&&q[c][j]===1&&i!==j)wanted.push([e,i,j]);
  }
  same(got,wanted,"independent separated-support ordering control");
  toyCases+=got.length;swappedCases+=got.filter(t=>t[1]>t[2]).length;toyInstances++;
 }
 insist(toyCases>0&&swappedCases>0,"orientation control coverage");
 const key=[2,5,[10,12,13]],A=makeMixed(2,1,1,[10,11,12]),B=makeMixed(5,1,1,[13,14]);
 insist(coefficientCertificate(key,A,B)===2,"actual surplus coefficient control");
 insist(coefficientCertificate([2,5,[10,12,99]],A,B)===null,"missing target edge detected");
 insist(coefficientCertificate(key,makeMixed(2,1,2,A.edges),B)===null,"wrong selector coefficient detected");
 insist(coefficientCertificate(key,makeMixed(3,1,1,A.edges),B)===null,"wrong selector variable detected");
 const overlapping=makeMixed(5,1,1,[10,13,14]);
 insist(coefficientCertificate(key,A,overlapping)===3,"overlapping mixed supports counted with multiplicity");
 let rejectedDuplicate=false;try{makeMixed(2,1,1,[10,10]);}catch(_){rejectedDuplicate=true;}
 insist(rejectedDuplicate,"duplicate source coefficient detected");
 insist(coefficientCertificate([2,5,[10,10,12,13]],A,B)===null,"repeated target coefficient rejected");
 let assignments=0,accepted=0;
 for(let xb=0;xb<=2;xb++)for(let xc=0;xc<=2;xc++)for(let y=0;y<=2;y++)for(let L=0;L<=2;L++)for(let R=0;R<=2;R++){
  if(y>xb||y>xc||L>xb||R>xc)continue;assignments++;
  if(y+L<=xb){insist(y+L+R<=xb+xc,"left continuous-grid consequence");accepted++;}
  if(y+R<=xc){insist(y+L+R<=xb+xc,"right continuous-grid consequence");accepted++;}
 }
 return {status:"PASS_INDEPENDENT_ORDER_AND_ACTUAL_COEFFICIENT_CONTROLS",toy_instances:toyInstances,toy_cases:toyCases,reversed_core_orientations:swappedCases,
  coefficient_checks:7,nonnegative_grid_assignments:assignments,valid_grid_implications:accepted,missing_q_premise_counterexample:[1,1,1,1,1],
  production_inputs_used:false,main_census_runs:0,optimizer_calls:0};
}
function run(configurationText,payload,codec,sourceText,codecText){
 const start=Date.now(),cfg=JSON.parse(configurationText),rows=[],cases=[],certificates=[],failures=[];
 const progress={stage:"bindings",core_pairs_completed:0,cases_constructed:0,cases_processed:0};
 let loaded=false,censusStart=null,censusSeconds=null,complete=false,keysHash=null,edgeHash=null,terms=0,zeroCases=0,emptyCases=0;
 let pairs=[],rowFlags=[],quotaLeft=0,quotaRight=0,quotaEither=0,targetCoefficientsChecked=0,selectorCoefficientsChecked=0,mixedCount=0;
 const histogram=new Map(),tickTotal=()=>insist(Date.now()-start<60000,"total 60 second limit");
 const tick=()=>{tickTotal();if(censusStart!==null)insist(Date.now()-censusStart<30000,"census 30 second limit");};
 try{
  insist(cfg.schema==="conway99.f0.four-exterior-cross-quota-independent-configuration.v1","configuration schema");
  same(cfg.limits,{census_ms:30000,total_ms:60000,report_bytes:16777216,cases:73404,rows:72468,certificates:144936},"fixed preparation limits");
  for(const [text,ref] of [[sourceText,cfg.source],[codecText,cfg.codec]]){
   const bytes=codec.utf8(text);insist(bytes.length===ref.bytes&&codec.sha256(bytes)===ref.sha256&&codec.gitBlob(bytes)===ref.git_blob_sha,"frozen implementation binding");
  }
  const data={};
  for(const name of ["domain","overlay"]){
   tickTotal();const ref=cfg.inputs[name],archive=codec.base64(payload[name]),raw=codec.gunzip(archive,4194304);
   insist(archive.length===ref.archive_bytes&&codec.sha256(archive)===ref.archive_sha256&&codec.gitBlob(archive)===ref.archive_git_blob,"archive binding "+name);
   insist(raw.length===ref.raw_bytes&&codec.sha256(raw)===ref.raw_sha256,"raw binding "+name);data[name]=JSON.parse(codec.ascii(raw));
  }
  loaded=true;censusStart=Date.now();progress.stage="independent_domain";
  const d=data.domain,o=data.overlay,h=d.signature_domain,q=d.row_targets,core=d.component_core_rows,n=h.length;
  insist(n===480&&core.length===21&&q.length===480&&d.complete_signature_count===480&&d.complete_possible_edge_count===68394,"complete domain dimensions");
  const masks=h.map(t=>{insist(t.length===3&&t.every((v,i)=>Number.isInteger(v)&&v>=0&&v<18&&(i===0||t[i-1]<v)),"sorted signature");return t.reduce((s,v)=>s|(1<<v),0);});
  const adjacency=core.slice(3).map(r=>r>>>3);
  for(let v=0;v<n;v++)for(let i=0;i<18;i++)insist(q[v][i]===2-((masks[v]>>>i)&1)-bits(adjacency[i]&masks[v]),"independent mixed quota formula");
  const edges=[],edgeIndex=new Int32Array(n*n).fill(-1),neighbors=Array.from({length:n},()=>[]),incident=Array.from({length:n},()=>[]);
  for(let a=0;a<n;a++){
   if((a&31)===0)tick();
   for(let b=a+1;b<n;b++){
    if(bits(masks[a]&masks[b])>1||!h[b].every(i=>q[a][i]>0)||!h[a].every(i=>q[b][i]>0))continue;
    const id=edges.length;edges.push([a,b]);edgeIndex[a*n+b]=edgeIndex[b*n+a]=id;
    neighbors[a].push(b);neighbors[b].push(a);incident[a].push(id);incident[b].push(id);
   }
  }
  insist(edges.length===68394,"independent complete edge count");same(neighbors,d.possible_neighbor_signature_ids,"independent neighbor domains");
  edgeHash=codec.sha256(codec.utf8(JSON.stringify(edges)));insist(edgeHash===o.complete_edge_order_sha256,"accepted original edge namespace");
  insist(o.status==="COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES"&&o.zero_rows.length===1884,"accepted literal-zero scope");
  const zero=new Uint8Array(edges.length);
  for(const z of o.zero_rows){
   insist(Number.isInteger(z.edge_id)&&z.edge_id>=0&&z.edge_id<edges.length&&!zero[z.edge_id]&&z.variable_index===540+z.edge_id,"distinct exact literal zero");
   zero[z.edge_id]=1;
  }
  const sharedSupports=new Map();
  for(let i=0;i<18;i++)for(let j=i+1;j<18;j++){
   if(((core[i+3]>>>(j+3))&1)!==0||bits(core[i+3]&core[j+3])!==0)continue;
   pairs.push([i,j]);const support=[];
   for(let a=0;a<n;a++)if((masks[a]&(1<<i))&&(masks[a]&(1<<j)))support.push(a);
   sharedSupports.set(18*i+j,support);sharedSupports.set(18*j+i,support);
  }
  insist(pairs.length===48,"complete separated core-pair class");tick();progress.stage="separated_support_cases";
  const tuples=separateCases(masks,q,pairs,edgeIndex,n,()=>{tick();progress.core_pairs_completed++;});
  progress.cases_constructed=tuples.length;insist(tuples.length===73404,"original complete case count");tick();
  const mixedCache=new Map(),rowIndex=new Map();
  function mixed(vertex,site){
   const index=18*vertex+site;if(mixedCache.has(index))return mixedCache.get(index);
   const support=[];
   for(const e of incident[vertex]){
    const [u,v]=edges[e],other=u===vertex?v:u;
    insist(u===vertex||v===vertex,"actual mixed incidence");
    if(masks[other]&(1<<site))support.push(e);
   }
   const M=makeMixed(vertex,site,q[vertex][site],support);mixedCache.set(index,M);mixedCount++;return M;
  }
  progress.stage="ordered_rows_and_actual_certificates";
  for(let caseId=0;caseId<tuples.length;caseId++){
   if((caseId&255)===0)tick();
   const [edge,i,j]=tuples[caseId],[b,c]=edges[edge],ql=q[b][j],qr=q[c][i];
   insist(b<c&&(masks[b]&(1<<i))&&!(masks[b]&(1<<j))&&(masks[c]&(1<<j))&&!(masks[c]&(1<<i))&&q[b][i]===1&&q[c][j]===1,"actual oriented premises");
   insist(ql>=1&&qr>=1,"eligible central cross quotas");
   if(zero[edge]){zeroCases++;cases.push([edge,i,j,-1,ql,qr,0]);progress.cases_processed++;continue;}
   const T=sharedSupports.get(18*i+j);insist(T!==undefined,"shared signature support");const left=[],right=[];
   for(const a of T){
    const l=edgeIndex[a*n+b],r=edgeIndex[a*n+c];
    if(l>=0&&!zero[l])left.push(l);if(r>=0&&!zero[r])right.push(r);
   }
   if(left.length===0||right.length===0){emptyCases++;cases.push([edge,i,j,-2,ql,qr,0]);progress.cases_processed++;continue;}
   const positive=[...new Set([edge,...left,...right])].sort((a,b)=>a-b),key=[b,c,positive],encoded=JSON.stringify(key);
   let id=rowIndex.get(encoded);
   if(id===undefined){insist(rows.length<cfg.limits.rows,"row storage bound");id=rows.length;rowIndex.set(encoded,id);rows.push(key);rowFlags.push(0);terms+=positive.length+2;}
   const hist=ql+","+qr;histogram.set(hist,(histogram.get(hist)||0)+1);let certificateMask=0;
   for(const side of [0,1]){
    if((side===0?ql:qr)!==1)continue;
    const site=side===0?j:i,A=mixed(b,site),B=mixed(c,site),residual=coefficientCertificate(key,A,B);
    insist(residual!==null,"proposed quota proof failed actual term/coefficient inspection");
    insist(certificates.length<cfg.limits.certificates,"certificate storage bound");
    certificates.push([caseId,side,A.index,B.index,residual]);certificateMask|=1<<side;
    targetCoefficientsChecked+=positive.length;selectorCoefficientsChecked+=2;
   }
   if(certificateMask&1)quotaLeft++;if(certificateMask&2)quotaRight++;if(certificateMask)quotaEither++;
   rowFlags[id]|=certificateMask;cases.push([edge,i,j,id,ql,qr,certificateMask]);progress.cases_processed++;
  }
  tick();insist(cases.length===73404&&zeroCases===936&&emptyCases===0&&rows.length===72468&&terms===1250496,"complete original inventory counts");
  insist(cases.filter(c=>c[3]>=0).length===rows.length,"all accepted row origins retained");
  progress.stage="ordered_key_acceptance_hash";keysHash=codec.sha256(codec.utf8(JSON.stringify(rows)));
  insist(keysHash===KEY_HASH&&cfg.original_acceptance.ordered_row_keys_sha256===KEY_HASH,"original accepted ordered row keys");
  tick();censusSeconds=(Date.now()-censusStart)/1000;complete=true;progress.stage="census_complete";
 }catch(error){failures.push({name:error.name,message:error.message,stage:progress.stage});if(censusStart!==null)censusSeconds=(Date.now()-censusStart)/1000;}
 const result={
  schema:SCHEMA,status:complete?"COMPLETE_INDEPENDENT_ORIGINAL_KEYS_AND_ACTUAL_CROSS_QUOTA_CERTIFICATES":"INCOMPLETE_CROSS_QUOTA_RECONSTRUCTION",complete,
  source:cfg.source,codec:cfg.codec,configuration_sha256:codec.sha256(codec.utf8(configurationText)),inputs:cfg.inputs,original_acceptance:cfg.original_acceptance,limits:cfg.limits,bindings_checked:loaded,progress,
  enumeration:"48 unordered core pairs and separated signature supports, orient central endpoints b<c, sort complete (edge_id,i,j) tuples",
  original_edge_order_sha256:edgeHash,core_pairs:pairs,case_count:cases.length,central_zero_cases:zeroCases,empty_side_cases:emptyCases,
  distinct_rows:rows.length,terms,ordered_row_keys_sha256:keysHash,row_keys:rows,
  row_key_fields:["b","c","sorted_positive_original_edge_ids"],row_inequality:"sum positive y - x_b - x_c <= 0",row_domain:[-2,0],
  selector_variable_offset:0,edge_variable_offset:540,case_fields:["central_edge_id","core_site_i","core_site_j","row_id_or_minus1_zero_minus2_empty","q_bj","q_ci","certificate_mask"],
  cases,complete_origins:"For each row r, all origin case IDs are exactly the array indices t with cases[t][3] === r.",
  certificate_fields:["origin_case_id","side_0_left_1_right","first_mixed_index","second_mixed_index","nonnegative_surplus_edge_coefficient_sum"],
  certificates,mixed_index_definition:"18*vertex+core_site; mixed row is sum over all original eligible incident edges whose other endpoint contains core_site, minus q_vertex,site*x_vertex = 0.",
  certificate_identity:"The target row equals the two indicated mixed equations minus their nonnegative surplus edge coefficients. Every target edge and both selector coefficients were inspected.",
  unique_mixed_rows_reconstructed:mixedCount,target_edge_coefficients_checked:targetCoefficientsChecked,selector_coefficients_checked:selectorCoefficientsChecked,
  cross_quota_histogram:[...histogram].map(([k,n])=>[...k.split(",").map(Number),n]).sort((a,b)=>a[0]-b[0]||a[1]-b[1]),
  left_sufficient_case_count:quotaLeft,right_sufficient_case_count:quotaRight,either_sufficient_case_count:quotaEither,
  rows_with_sufficient_mixed_certificate:rowFlags.filter(v=>v!==0).length,row_certificate_masks:rowFlags,
  retained_row_ids:rowFlags.map((flag,index)=>flag===0?index:-1).filter(index=>index>=0),
  retained_row_ids_are_provisional_until_independent_certificate_acceptance:true,complete_original_row_keys_are_preserved:true,
  failed_sufficient_test_is_not_nonredundancy:true,census_seconds:censusSeconds,seconds_before_serialization:(Date.now()-start)/1000,
  failures,previous_failed_attempt_repeated:false,old_producer_imported_or_executed:false,original_gzip_inventory_recovered:false,
  independent_terminal_acceptance_not_claimed:true,optimizer_calls:0,native_model_builds:0,graph_constructed:false,whole_component_excluded:false
 };
 let serialized=JSON.stringify(result)+"\n",bytes=codec.utf8(serialized).length,elapsed=(Date.now()-start)/1000;
 if(bytes>cfg.limits.report_bytes||elapsed*1000>=cfg.limits.total_ms){
  result.complete=false;result.status="INCOMPLETE_CROSS_QUOTA_RECONSTRUCTION";
  result.failures.push({name:"FinalizationLimit",message:"serialization exceeded total time or report byte bound",stage:"serialization"});
  serialized=JSON.stringify(result)+"\n";bytes=codec.utf8(serialized).length;elapsed=(Date.now()-start)/1000;
 }
 return {result,serialized,finalization:{complete_within_declared_bounds:result.complete,census_seconds:censusSeconds,total_seconds:elapsed,serialized_bytes:bytes,
  publication_hashes_computed_inside_main:false,limits:cfg.limits}};
}
return {controls,run};
})()