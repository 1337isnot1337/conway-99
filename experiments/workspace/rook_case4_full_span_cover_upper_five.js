/* Conway99 case4: exact H42 parity/upper-five theorem and native upper-capacity projection.
Inputs are the two immutable public UTF-8 JSON files listed in BINDINGS.
No network, optimizer, native model, or full coordinate-cover reconstruction. */
(() => {
"use strict";
const BINDINGS={native_sha256:"a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476",native_git:"89fece302243da184766735c7517aa67f00a0dbe",face_sha256:"c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3",face_git:"f59c25b741406acb77ccad26bab9c51e9f7bf9e2"};
const H=[28,47,48,50,80,127,129,130,131,179,180,182,230,266,344,407,466,545,597,598,602,605,664,665,668,669,670,736,769,807,851,918,919,967,971,972,974,976,978,980,1016,1017], PARITY_ROWS=[93,102,117,118,119,121,122,123,124,156,186,215,224,235,236,237,238,239,240,241,296,301,321,326,330,337,338,340,341,342,343,344,350,373,377,382,385,387,388,389,411,416,436,455,473,521,535,548,560,571], UPPER_ROWS=[368,411,431,590];
function assert(ok,message){if(!ok)throw Error(message);}
function eq(a,b){return JSON.stringify(a)===JSON.stringify(b);}
function data(nativeText,faceText,hash){
 assert(hash.sha256(nativeText)===BINDINGS.native_sha256,"native raw binding");
 assert(hash.sha256(faceText)===BINDINGS.face_sha256,"face raw binding");
 const native=JSON.parse(nativeText),face=JSON.parse(faceText),I=native.primary_inventory,Z=face.fixed_zero_columns;
 assert(native.primary_inventory_sha256===face.primary_inventory_sha256,"inventory link");
 assert(I.Gram_rows.length===630 && I.original_signature_rows.length===186 && I.triple_rows.length===1365 && I.Gram_conflict_clauses.length===30 && I.uncapped_integer_cuts.length===60,"complete native inventory");
 assert(face.original_columns===1214 && face.columns===1102 && Z.length===112 && new Set(Z).size===112,"face size");
 assert(H.length===42 && new Set(H).size===42 && H.every(a=>!Z.includes(a)),"H domain");
 for(const r of I.Gram_rows){assert(r.length===4 && Number.isSafeInteger(r[2]) && r[2]>=0,"Gram row");assert(new Set(r[3]).size===r[3].length && r[3].every(a=>Number.isSafeInteger(a)&&a>=0&&a<1214),"Gram support");}
 return {I,Z,native,face};
}
function theorem(D){
 const {I,Z}=D,zs=new Set(Z),hs=new Set(H),c=Array(1214).fill(0);let b=0;
 for(const id of PARITY_ROWS){b+=I.Gram_rows[id][2];for(const a of I.Gram_rows[id][3])c[a]++;}
 assert(b===81,"parity RHS");
 const odd=c.map((v,a)=>[a,v]).filter(([a,v])=>(v&1)&&!zs.has(a)).map(([a])=>a);
 assert(eq(odd,H),"full original-coordinate parity lift");
 const removed=c.map((v,a)=>[a,v]).filter(([a,v])=>(v&1)&&zs.has(a)).map(([a])=>a);
 const u=Array(1214).fill(0);let ub=0;
 for(const id of UPPER_ROWS){ub+=I.Gram_rows[id][2];for(const a of I.Gram_rows[id][3])u[a]++;}
 assert(ub===5,"upper RHS");
 const residual=u.map((v,a)=>v-(hs.has(a)?1:0));
 assert(residual.every(v=>Number.isSafeInteger(v)&&v>=0),"nonnegative residual on all1214");
 const positive=residual.map((v,a)=>[a,v]).filter(([a,v])=>v>0),newZeros=positive.filter(([a])=>!zs.has(a)).map(([a])=>a);
 assert(H.every(a=>I.Gram_rows[585][3].includes(a)) && I.Gram_rows[585][2]===7,"old degree bound");
 return {schema:"rook-case4-H42-original-Gram-upper-five-v1",bindings:BINDINGS,H,parity:{original_row_ids:PARITY_ROWS,full1214_coefficients:c,rhs:b,removed_odd_zero_columns:removed,active_capacity_terms:c.map((v,a)=>[a,Math.floor(v/2)]).filter(([a,v])=>v>0&&!zs.has(a)),capacity_upper:40},upper:{original_row_ids:UPPER_ROWS,rows:UPPER_ROWS.map(id=>({id,core_pair:I.Gram_rows[id].slice(0,2),quota:I.Gram_rows[id][2]})),full1214_coefficients:u,rhs:ub,full1214_residual:residual,positive_residual_terms:positive},conclusion:{nonnegative_real_Gram_bound:"sum_H x <= 5",integer_parity_after_only_listed_odd_zero_substitutions:1,possible_nonnegative_integer_values:[1,3,5]},conditional_H_equals_five:{all_positive_residual_zero_columns:positive.map(([a])=>a),prior_global_zero_columns:Z,new_zero_columns:newZeros,new_H_zero_columns:newZeros.filter(a=>hs.has(a)),scope:"Conditional only. H=5 and the four original Gram equalities force these zeros by nonnegativity."},does_not_claim_case4_exclusion:true};
}
function upperRows(D){
 const I=D.I,hs=new Set(H),rows=[];
 function add(kind,id,upper,support,extra){const s=support.filter(a=>hs.has(a));if(s.length>upper)rows.push({kind,id,upper,support:s,...extra});}
 I.Gram_rows.forEach((r,id)=>add("Gram",id,r[2],r[3],{core_pair:r.slice(0,2)}));
 I.original_signature_rows.forEach((r,id)=>add("signature",id,1,r[1],{signature:r[0]}));
 I.triple_rows.forEach((r,id)=>add("triple",id,1,r.members,{core_triple:r.triple}));
 I.Gram_conflict_clauses.forEach((r,id)=>{assert(r.every(v=>v<0),"all-negative conflict");add("conflict",id,r.length-1,r.map(v=>-v-1),{});});
 const by=new Map();for(const r of rows){const k=r.upper+":"+r.support.join(",");if(!by.has(k))by.set(k,{...r,all_provenance:[]});by.get(k).all_provenance.push({kind:r.kind,id:r.id});}
 return {projected_rows_before_dedup:rows,deduplicated_rows:[...by.values()]};
}
function census(D,limits={nodes:1000000,milliseconds:10000}){
 const started=Date.now(),U=upperRows(D),rows=U.deduplicated_rows.filter(r=>r.upper<7),pos=new Map(H.map((a,i)=>[a,i]));
 const memberships=H.map(()=>[]),counts=rows.map(()=>0),subsets=Array.from({length:8},()=>[]),rejectionByRow=rows.map(()=>0);
 rows.forEach((r,id)=>r.support.forEach(a=>memberships[pos.get(a)].push(id)));
 let nodes=0,tests=0,complete=true,stopReason=null;const selected=[];
 function step(start){
  if(++nodes>limits.nodes || Date.now()-started>limits.milliseconds){complete=false;stopReason="finite resource bound";return;}
  subsets[selected.length].push(selected.map(i=>H[i]));
  if(selected.length===7)return;
  for(let i=start;i<H.length;i++){tests++;let bad=-1;for(const r of memberships[i])if(counts[r]===rows[r].upper){bad=r;break;}
   if(bad>=0){rejectionByRow[bad]++;continue;}
   for(const r of memberships[i])counts[r]++;selected.push(i);step(i+1);selected.pop();for(const r of memberships[i])counts[r]--;if(!complete)return;
  }
 }
 step(0);
 return {schema:"rook-case4-H42-native-upper-projection-v1",complete,stopReason,scope:"All subsets of H of size at most seven obeying all original Gram/signature/triple/conflict upper capacities. Omitted selectors remain free; no projection-lifting claim. No uncapped signed-row propagation or full coordinate-cover census.",counts:subsets.map(a=>a.length),subsets,rows:U,rejections:rows.map((r,i)=>({kind:r.kind,id:r.id,upper:r.upper,rejected_extensions:rejectionByRow[i]})).filter(r=>r.rejected_extensions),nodes,tests,limits};
}
return {BINDINGS,H,PARITY_ROWS,UPPER_ROWS,data,theorem,upperRows,census};
})()
