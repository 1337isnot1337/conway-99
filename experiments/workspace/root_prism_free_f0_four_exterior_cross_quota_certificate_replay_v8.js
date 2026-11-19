(() => {
"use strict";
function need(ok,message){if(!ok)throw Error(message);}
function same(a,b,message){need(JSON.stringify(a)===JSON.stringify(b),message);}
function pop(x){let n=0;while(x){x&=x-1;n++;}return n;}
function residualCertificate(first,second,target){
 const v=new Map();
 for(const [x,c] of first.concat(second))v.set(x,(v.get(x)||0)+c);
 for(const [x,c] of target)v.set(x,(v.get(x)||0)-c);
 let sum=0;
 for(const [x,c] of v){
  if(x<540){if(c!==0)return null;}
  else {if(c<0)return null;sum+=c;}
 }
 return sum;
}
function controls(){
 const A=[[2,-1],[550,1],[551,1]],B=[[5,-1],[550,1],[553,1]];
 const target=[[2,-1],[5,-1],[550,1],[553,1]];
 need(residualCertificate(A,B,target)===2,"surplus with repeated source edge");
 need(residualCertificate(A,B,[[2,-1],[5,-1],[550,1],[554,1]])===null,"missing target edge rejected");
 need(residualCertificate([[2,-2],[550,1],[551,1]],B,target)===null,"selector multiplier rejected");
 need(residualCertificate(A,[[6,-1],[550,1],[553,1]],target)===null,"selector name rejected");
 need(residualCertificate(A,B,[[2,-1],[5,-1],[550,3],[553,1]])===null,"target multiplicity rejected");
 return {status:"PASS_INDEPENDENT_SPARSE_LINEAR_CERTIFICATE_CONTROLS",checks:5,source_duplicate_coefficient_accumulated:true};
}
function verify(report,domain,overlay,sha256Text){
 const start=Date.now(),tick=()=>need(Date.now()-start<30000,"artifact certificate replay deadline");
 need(report.complete===true&&report.status==="COMPLETE_INDEPENDENT_ORIGINAL_KEYS_AND_ACTUAL_CROSS_QUOTA_CERTIFICATES","completed compact report");
 need(report.row_keys.length===72468&&report.cases.length===73404&&report.central_zero_cases===936&&report.empty_side_cases===0,"complete original scope");
 const rowHash=sha256Text(JSON.stringify(report.row_keys));
 need(rowHash==="2adfcc619820604a3f49463bd0fd8109113ab7ce13bceadcc49554533b09dd1c"&&rowHash===report.ordered_row_keys_sha256,"full original ordered keys");
 const h=domain.signature_domain,core=domain.component_core_rows,neighbors=domain.possible_neighbor_signature_ids;
 need(h.length===480&&core.length===21,"domain");
 const masks=h.map(t=>t.reduce((s,i)=>s|(1<<i),0));
 const q=masks.map(m=>Array.from({length:18},(_,i)=>2-((m>>>i)&1)-pop((core[i+3]>>>3)&m)));
 same(q,domain.row_targets,"all accepted mixed coefficients");
 const edges=[],indices=new Map();
 for(let a=0;a<480;a++)for(const b of neighbors[a])if(a<b){indices.set(a+","+b,edges.length);edges.push([a,b]);}
 need(edges.length===68394&&sha256Text(JSON.stringify(edges))==="411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb","parent native edge namespace");
 const edgeId=(a,b)=>indices.get(a<b?a+","+b:b+","+a);
 const zeros=new Set();
 for(const row of overlay.zero_rows){need(row.variable_index===540+row.edge_id&&!zeros.has(row.edge_id),"old zero proof identity");zeros.add(row.edge_id);}
 need(zeros.size===1884,"zero scope");
 const originCount=new Uint8Array(72468),expectedFlags=new Uint8Array(72468),actualFlags=new Uint8Array(72468),certMasks=new Uint8Array(73404);
 let live=0,zero=0,terms=0,previous=[-1,-1,-1];
 for(let t=0;t<report.cases.length;t++){
  if((t&511)===0)tick();
  const [e,i,j,rid,ql,qr,flag]=report.cases[t];
  need([e,i,j,rid,ql,qr,flag].every(Number.isInteger)&&e>=0&&e<edges.length&&i>=0&&i<18&&j>=0&&j<18&&i!==j,"case integers");
  need(e>previous[0]||(e===previous[0]&&(i>previous[1]||(i===previous[1]&&j>previous[2]))),"strict original case order");previous=[e,i,j];
  const [b,c]=edges[e],both=(1<<i)|(1<<j);
  need((masks[b]&(1<<i))&&!(masks[b]&(1<<j))&&(masks[c]&(1<<j))&&!(masks[c]&(1<<i)),"oriented core membership");
  need(q[b][i]===1&&q[c][j]===1&&ql===q[b][j]&&qr===q[c][i]&&ql>=1&&qr>=1,"actual original and cross quotas");
  need(!((core[i+3]>>>(j+3))&1)&&pop(core[i+3]&core[j+3])===0,"original full-core pair class");
  if(zeros.has(e)){need(rid===-1&&flag===0,"exact zero-case disposition");zero++;continue;}
  need(rid===live++&&originCount[rid]===0,"one ordered original origin per row");originCount[rid]++;
  const positive=new Set([e]);let left=0,right=0;
  for(const [center,side] of [[b,0],[c,1]])for(const other of neighbors[center]){
   if((masks[other]&both)!==both)continue;const p=edgeId(center,other);
   need(Number.isInteger(p),"saved neighbor edge");
   if(!zeros.has(p)){positive.add(p);if(side===0)left++;else right++;}
  }
  need(left>0&&right>0,"both live original stars");
  const key=[b,c,[...positive].sort((a,b)=>a-b)];
  same(key,report.row_keys[rid],"complete original row key reconstructed at "+rid);
  terms+=key[2].length+2;
  const expected=Number(ql===1)+2*Number(qr===1);
  need(flag===expected,"complete sufficient quota mask");
  expectedFlags[rid]=expected;
 }
 need(live===72468&&zero===936&&terms===1250496&&originCount.every(x=>x===1),"all original rows and origins");
 const mixedCache=new Map();
 function mixed(index){
  need(Number.isInteger(index)&&index>=0&&index<8640,"native mixed row offset");
  if(mixedCache.has(index))return mixedCache.get(index);
  const center=Math.floor(index/18),site=index%18,terms=[];
  if(q[center][site])terms.push([center,-q[center][site]]);
  for(const other of neighbors[center])if(masks[other]&(1<<site))terms.push([540+edgeId(center,other),1]);
  mixedCache.set(index,terms);return terms;
 }
 let totalSurplus=0,certificates=0;
 for(const record of report.certificates){
  if((certificates&511)===0)tick();
  need(record.length===5&&record.every(Number.isInteger),"certificate format");
  const [caseId,side,m1,m2,surplus]=record;
  need(caseId>=0&&caseId<73404&&(side===0||side===1),"certificate origin");
  const [e,i,j,rid,ql,qr,flag]=report.cases[caseId];need(rid>=0,"live certificate target");
  const bit=1<<side;need((flag&bit)!==0&&(certMasks[caseId]&bit)===0,"one certificate per promised recipe");
  const [b,c,positive]=report.row_keys[rid],site=side===0?j:i;
  need(m1===18*b+site&&m2===18*c+site,"actual native row recipe");
  const target=[[b,-1],[c,-1],...positive.map(edge=>[540+edge,1])];
  const actual=residualCertificate(mixed(m1),mixed(m2),target);
  need(actual!==null&&actual===surplus,"independent complete sparse coefficient certificate");
  totalSurplus+=actual;certMasks[caseId]|=bit;actualFlags[rid]|=bit;certificates++;
 }
 for(let t=0;t<73404;t++)need(certMasks[t]===report.cases[t][6],"every promised case certificate checked");
 same([...actualFlags],[...expectedFlags],"every row sufficient-proof mask");
 same([...actualFlags],report.row_certificate_masks,"saved row flags");
 const retained=[];for(let r=0;r<72468;r++)if(actualFlags[r]===0)retained.push(r);
 same(retained,report.retained_row_ids,"every retained original row ID");
 need(72468-retained.length===report.rows_with_sufficient_mixed_certificate,"complete deletion count");
 tick();
 return {schema:"conway99.f0.four-exterior-cross-quota-artifact-certificate-replay.v1",status:"PASS_EVERY_ORIGINAL_ROW_ORIGIN_AND_MIXED_LINEAR_CERTIFICATE",
  complete_original_rows:72468,complete_original_cases:73404,complete_original_terms:1250496,central_zero_cases:936,
  ordered_row_keys_sha256:rowHash,complete_coefficients_checked_for_certificates:certificates,nonnegative_surplus_coefficient_sum:totalSurplus,
  unique_native_mixed_rows_reconstructed:mixedCache.size,native_mixed_row_start:154430,
  rows_implied_by_two_original_mixed_equations:72468-retained.length,retained_rows:retained.length,retained_row_ids:retained,
  retained_row_ids_sha256:sha256Text(JSON.stringify(retained)),all_case_and_row_masks_compared:true,
  parent_native_mixed_equations_are_previously_independently_accepted_premises:true,
  old_producer_or_compact_producer_imported:false,original_compressed_inventory_recovered:false,
  unproved_nonredundancy_of_retained_rows:false,optimizer_calls:0,native_model_builds:0,seconds:(Date.now()-start)/1000,
  maximum_ms:30000,graph_constructed:false,whole_component_excluded:false};
}
return {controls,verify};
})()