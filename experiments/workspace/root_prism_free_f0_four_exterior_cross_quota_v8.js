(() => {
"use strict";
function assert(ok,message){if(!ok)throw Error(message);}
function pop(n){let count=0;while(n){n&=n-1;count++;}return count;}
function compareRows(a,b){if(a[0]!==b[0])return a[0]-b[0];if(a[1]!==b[1])return a[1]-b[1];const x=a[2],y=b[2];for(let i=0;i<Math.min(x.length,y.length);i++)if(x[i]!==y[i])return x[i]-y[i];return x.length-y.length;}
function controls(){
 let left=0,right=0,checked=0;
 for(let xb=0;xb<2;xb++)for(let xc=0;xc<2;xc++)for(let y=0;y<2;y++)for(let L=0;L<2;L++)for(let R=0;R<2;R++){
  if(y>xb||y>xc||L>xb||R>xc)continue;checked++;
  if(y+L<=xb){assert(y+L+R<=xb+xc,"left cross-quota");left++;}
  if(y+R<=xc){assert(y+L+R<=xb+xc,"right cross-quota");right++;}
 }
 assert(1+1+1>1+1,"missing cross-quota counterexample");
 return {status:"PASS_CROSS_QUOTA_SUFFICIENT_IMPLICATION_CONTROLS",activation_assignments:checked,left_cases:left,right_cases:right,missing_premise_counterexample:[1,1,1,1,1]};
}
function run(domain,overlay,sha256Text){
 const start=Date.now(),maximumMs=30000;const tick=()=>assert(Date.now()-start<maximumMs,"cross-quota census deadline");
 const h=domain.signature_domain,q=domain.row_targets,core=domain.component_core_rows;
 assert(h.length===480&&core.length===21,"domain dimensions");
 const masks=h.map(t=>t.reduce((s,i)=>s|(1<<i),0)),edges=[];
 for(let a=0;a<480;a++)for(const b of domain.possible_neighbor_signature_ids[a])if(a<b)edges.push([a,b]);
 assert(edges.length===68394&&sha256Text(JSON.stringify(edges))===overlay.complete_edge_order_sha256,"exact edge order");
 const ids=new Map(edges.map((e,i)=>[e.join(","),i])),zeros=new Set(overlay.zero_rows.map(r=>r.edge_id));
 assert(zeros.size===1884,"zero family");
 const edgeId=(a,b)=>{if(a>b)[a,b]=[b,a];return ids.get(a+","+b);};
 const pairs=[];for(let i=0;i<18;i++)for(let j=i+1;j<18;j++)
  if(!((core[i+3]>>>(j+3))&1)&&pop(core[i+3]&core[j+3])===0)pairs.push([i,j]);
 assert(pairs.length===48,"complete Gij2 pair set");
 const pairKey=(i,j)=>i<j?i+","+j:j+","+i;
 const pairSet=new Set(pairs.map(p=>p.join(","))),stars=new Map();
 for(const [i,j]of pairs){
  const support=[];for(let a=0;a<480;a++)if((masks[a]&(1<<i))&&(masks[a]&(1<<j)))support.push(a);
  stars.set(i+","+j,support);
 }
 let cases=0,centralZero=0,emptySide=0,quotaCases=0,quotaLeft=0,quotaRight=0;
 const rows=new Map(),caseCounts={};
 for(let e=0;e<edges.length;e++){
  if((e&1023)===0)tick();const [b,c]=edges[e];
  for(const i of h[b])for(const j of h[c]){
   if((masks[b]&(1<<j))||(masks[c]&(1<<i))||q[b][i]!==1||q[c][j]!==1||!pairSet.has(pairKey(i,j)))continue;
   const caseId=cases++;if(zeros.has(e)){centralZero++;continue;}
   const T=stars.get(pairKey(i,j));
   const left=T.map(a=>edgeId(a,b)).filter(e=>e!==undefined&&!zeros.has(e));
   const right=T.map(a=>edgeId(a,c)).filter(e=>e!==undefined&&!zeros.has(e));
   if(left.length===0||right.length===0){emptySide++;continue;}
   const positive=[...new Set([e,...left,...right])].sort((x,y)=>x-y),key=[b,c,positive],encoded=JSON.stringify(key);
   const l=q[b][j]<=1,r=q[c][i]<=1;
   assert(q[b][j]>=1&&q[c][i]>=1,"eligible central cross-quotas");
   if(l)quotaLeft++;if(r)quotaRight++;if(l||r)quotaCases++;
   const hist=q[b][j]+","+q[c][i];caseCounts[hist]=(caseCounts[hist]||0)+1;
   if(!rows.has(encoded))rows.set(encoded,{key,origins:[],linear_mixed_quota_proofs:[]});
   const row=rows.get(encoded);row.origins.push({case_id:caseId,core_sites:[i,j],edge_id:e,left_edges:left,right_edges:right,cross_quotas:[q[b][j],q[c][i]]});
   if(l)row.linear_mixed_quota_proofs.push({case_id:caseId,kind:"mixed_b_j_plus_right_side_bound",native_mixed_rows:[154430+18*b+j,154430+18*c+j]});
   if(r)row.linear_mixed_quota_proofs.push({case_id:caseId,kind:"left_side_bound_plus_mixed_c_i",native_mixed_rows:[154430+18*c+i,154430+18*b+i]});
  }
 }
 const ordered=[...rows.values()],keys=ordered.map(r=>r.key);
 const keysHash=sha256Text(JSON.stringify(keys));
 assert(cases===73404&&centralZero===936&&emptySide===0&&ordered.length===72468,"original complete counts");
 assert(keysHash==="2adfcc619820604a3f49463bd0fd8109113ab7ce13bceadcc49554533b09dd1c","original independently accepted ordered keys");
 let terms=0;for(const row of ordered)terms+=row.key[2].length+2;
 assert(terms===1250496,"original complete terms");tick();
 return {schema:"conway99.f0.four-exterior-cross-quota-replay.v1",status:"COMPLETE_ORIGINAL_ROW_KEYS_REBUILT_AND_CROSS_QUOTAS_CLASSIFIED",
  core_pairs:pairs,cases,central_zero_cases:centralZero,empty_side_cases:emptySide,distinct_rows:ordered.length,terms,ordered_row_keys_sha256:keysHash,
  original_keys_match_pre_outage_independent_acceptance:true,cross_quota_case_histogram:caseCounts,
  left_quota_one_cases:quotaLeft,right_quota_one_cases:quotaRight,one_or_both_cross_quota_one_cases:quotaCases,
  rows_with_sufficient_linear_mixed_proof:ordered.filter(r=>r.linear_mixed_quota_proofs.length>0).length,
  complete_rows_and_origins:ordered,seconds:(Date.now()-start)/1000,maximum_ms:maximumMs,
  original_compressed_inventory_recovered:false,original_metadata_failure_rewritten:false,
  optimizer_calls:0,native_model_builds:0,whole_component_excluded:false};
}
return {controls,run};
})()