/* Conditional H=5 branch continuation. Exactly the frozen 996 native-capacity five-sets.
This wrapper consumes the separately source-bound native propagation engine and full row ledger.
All exclusions concern the stated H pattern only; no native optimizer is used. */
(() => {
"use strict";
const LIMITS={batch_milliseconds:60000,branch_milliseconds:1000,replay_milliseconds:60000,transcript_bytes:67108864,maximum_row_visits_per_branch:3000000,maximum_branches:996};
function assert(b,m){if(!b)throw Error(m);}
function seedsFor(theorem,pattern){
 const H=theorem.H,s=new Set(pattern),x=new Map();
 assert(pattern.length===5&&s.size===5&&pattern.every(a=>H.includes(a)),"five-set");
 function put(a,v){assert(!x.has(a)||x.get(a)===v,"premise conflict");x.set(a,v);}
 for(const a of theorem.conditional_H_equals_five.prior_global_zero_columns)put(a,0);
 for(const a of theorem.conditional_H_equals_five.new_zero_columns)put(a,0);
 for(const a of H)put(a,s.has(a)?1:0);
 return [...x].sort((a,b)=>a[0]-b[0]);
}
function run(rows,theorem,census,engine){
 assert(rows.length===2272&&census.complete&&census.subsets[5].length===996,"frozen scope");
 const started=Date.now(),records=[];let bytes=0,stop="complete";
 for(let id=0;id<census.subsets[5].length;id++){
  const remaining=LIMITS.batch_milliseconds-(Date.now()-started);
  if(remaining<=0){stop="shared time bound";break;}
  const pattern=census.subsets[5][id],seeds=seedsFor(theorem,pattern);
  const r=engine.propagate(rows,seeds,{milliseconds:Math.min(remaining,LIMITS.branch_milliseconds),maximum_row_visits:LIMITS.maximum_row_visits_per_branch});
  const record={id,pattern,terminal:r.terminal,trace:r.trace.map(t=>[t.row,t.variable,t.value]),final_zero_count:r.assignment.filter(v=>v===0).length,final_one_count:r.assignment.filter(v=>v===1).length,row_visits:r.row_visits};
  const size=JSON.stringify(record).length+1;
  if(bytes+size>LIMITS.transcript_bytes){stop="transcript bound before acceptance";break;}
  records.push(record);bytes+=size;
  if(r.terminal.status==="partial"){stop="first partial branch";break;}
 }
 return {schema:"rook-case4-H42-H5-native-branches-v1",complete:records.length===996&&records.every(r=>r.terminal.status!=="partial"),scope:"112 proved global zeros; H=5; full2271 original native constraints; no coordinate-cover registry",limits:LIMITS,stop,records,completed_patterns:records.length,contradictions:records.filter(r=>r.terminal.status.startsWith("contradiction")).length,noncontradictory_fixed_points:records.filter(r=>r.terminal.status==="fixed_point").length,trace_forces:records.reduce((s,r)=>s+r.trace.length,0),transcript_bytes:bytes,elapsed_ms:Date.now()-started,optimizer_calls:0};
}
function verifyOne(rows,theorem,record){
 const x=Array(1214).fill(-1);
 for(const [a,v]of seedsFor(theorem,record.pattern))x[a]=v;
 function bounds(row,overrideA=-1,overrideV=-1){
  let lower=0,upper=0;
  for(const [a,c]of row.terms){const v=a===overrideA?overrideV:x[a];if(v===0)continue;if(v===1){lower+=c;upper+=c;}else if(c>=0)upper+=c;else lower+=c;}
  return [lower,upper];
 }
 function excluded(row,l,u){return u<row.lower||l>row.upper;}
 for(const t of record.trace){
  assert(t.length===3&&t.every(Number.isSafeInteger),"trace integer triple");
  const [rid,a,v]=t;assert(rid>=0&&rid<rows.length&&a>=0&&a<1214&&(v===0||v===1)&&x[a]<0,"fresh forced bit");
  const row=rows[rid];assert(row.terms.some(([b])=>b===a),"present coefficient");
  const [l,u]=bounds(row);assert(!excluded(row,l,u),"no earlier row contradiction");
  const [ol,ou]=bounds(row,a,1-v);assert(excluded(row,ol,ou),"opposite branch impossible");
  x[a]=v;
 }
 assert(x.filter(v=>v===0).length===record.final_zero_count&&x.filter(v=>v===1).length===record.final_one_count,"final counts");
 const z=record.terminal;
 if(z.status==="contradiction"){
  const row=rows[z.row],[l,u]=bounds(row);assert(l===z.lo&&u===z.hi&&excluded(row,l,u),"terminal row contradiction");
 }else if(z.status==="contradiction_by_binary_split"){
  assert(x[z.variable]<0,"free split coordinate");
  for(const v of [0,1]){const [l,u]=bounds(rows[z.row],z.variable,v);assert(excluded(rows[z.row],l,u),"terminal split contradiction");}
 }else if(z.status==="fixed_point"){
  for(const row of rows){
   const [l,u]=bounds(row);assert(!excluded(row,l,u),"fixed point row");
   for(const [a,c]of row.terms)if(x[a]<0){
    const l0=l-(c<0?c:0),u0=u-(c>0?c:0);
    assert(!excluded(row,l0,u0)&&!excluded(row,l0+c,u0+c),"fixed point has no native forced literal");
   }
  }
 }else assert(z.status==="partial","known terminal");
 return {id:record.id,status:"PASS",terminal:z.status,forces:record.trace.length};
}
function replay(rows,theorem,census,result){
 const started=Date.now(),checks=[];
 assert(result.records.length<=996,"finite record prefix");
 for(let id=0;id<result.records.length;id++){
  if(Date.now()-started>LIMITS.replay_milliseconds)return {status:"partial replay",checked:checks.length,checks,elapsed_ms:Date.now()-started};
  const r=result.records[id];assert(r.id===id&&JSON.stringify(r.pattern)===JSON.stringify(census.subsets[5][id]),"exact prescribed prefix");
  checks.push(verifyOne(rows,theorem,r));
 }
 assert(result.complete=== (result.records.length===996&&result.records.every(r=>r.terminal.status!=="partial")),"complete flag");
 return {status:"PASS",checked:checks.length,checks,all_full_native_fixed_points_checked:true,elapsed_ms:Date.now()-started,optimizer_calls:0};
}
return {LIMITS,seedsFor,run,verifyOne,replay};
})()
