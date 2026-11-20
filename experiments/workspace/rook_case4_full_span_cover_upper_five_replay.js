/* Independent direct replay of the case4 H42 upper-five theorem and its finite native projection. */
(() => {
"use strict";
const assert=(p,m)=>{if(!p)throw Error(m);};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function arithmetic(native,face,proof) {
 const I=native.primary_inventory, H=proof.H, Z=new Set(face.fixed_zero_columns);
 assert(native.primary_inventory_sha256===face.primary_inventory_sha256,"inventory ancestry");
 assert(H.length===42 && new Set(H).size===42 && H.every((a,i)=>Number.isInteger(a)&&a>=0&&a<1214&&!Z.has(a)&&(i===0||H[i-1]<a)),"H domain");
 assert(Z.size===112 && face.original_columns===1214,"face");
 const lift=ids=>{const v=Array(1214).fill(0);let rhs=0;assert(new Set(ids).size===ids.length,"distinct Gram rows");for(const id of ids){const r=I.Gram_rows[id];assert(r&&r[2]>=0&&Number.isSafeInteger(r[2]),"original row");rhs+=r[2];for(const a of r[3])v[a]++;}return {v,rhs};};
 const parity=lift(proof.parity.original_row_ids), upper=lift(proof.upper.original_row_ids);
 assert(parity.rhs===81 && parity.rhs===proof.parity.rhs,"parity right side");
 assert(same(parity.v,proof.parity.full1214_coefficients),"parity coefficient vector");
 const odd=parity.v.flatMap((c,a)=>c%2&&!Z.has(a)?[a]:[]);
 assert(same(odd,H),"odd support");
 assert(same(parity.v.flatMap((c,a)=>c%2&&Z.has(a)?[a]:[]),proof.parity.removed_odd_zero_columns),"removed odd zeros");
 assert(same(upper.v,proof.upper.full1214_coefficients)&&upper.rhs===5&&proof.upper.rhs===5,"upper coefficient vector");
 const hs=new Set(H),residual=upper.v.map((v,a)=>v-(hs.has(a)?1:0));
 assert(residual.every(v=>v>=0)&&same(residual,proof.upper.full1214_residual),"nonnegative residual");
 const terms=residual.flatMap((v,a)=>v?[[a,v]]:[]);
 assert(same(terms,proof.upper.positive_residual_terms),"residual terms");
 const fresh=terms.filter(([a])=>!Z.has(a)).map(([a])=>a);
 assert(same(fresh,proof.conditional_H_equals_five.new_zero_columns),"conditional zeros");
 assert(same(fresh.filter(a=>hs.has(a)),proof.conditional_H_equals_five.new_H_zero_columns),"conditional H zeros");
 assert(same(proof.conclusion.possible_nonnegative_integer_values,[1,3,5]),"odd range");
 return {all_original_coordinates_checked:1214,parity_rows:proof.parity.original_row_ids.length,parity_rhs:parity.rhs,upper_rows:proof.upper.original_row_ids.length,upper_rhs:upper.rhs,positive_residual_columns:terms.length,new_conditional_zeros:fresh.length,new_conditional_H_zeros:fresh.filter(a=>hs.has(a))};
}
function projection(native,proof,record) {
 const I=native.primary_inventory,H=proof.H,hs=new Set(H),rows=[];
 const add=(s,u)=>{assert(Number.isInteger(u)&&u>=0&&new Set(s).size===s.length,"upper row");const t=s.filter(a=>hs.has(a));if(t.length>u)rows.push({s:t,u});};
 I.Gram_rows.forEach(r=>add(r[3],r[2]));
 I.original_signature_rows.forEach(r=>add(r[1],1));
 I.triple_rows.forEach(r=>add(r.members,1));
 I.Gram_conflict_clauses.forEach(r=>{assert(r.every(v=>v<0),"negative conflict");add(r.map(v=>-v-1),r.length-1);});
 assert(record.complete===true&&record.subsets.length===8&&same(record.subsets[0],[[]]),"complete root level");
 const key=s=>s.join(","), valid=s=>{const chosen=new Set(s);return rows.every(r=>r.s.reduce((n,a)=>n+Number(chosen.has(a)),0)<=r.u);};
 let extensions=0;
 for(let level=0;level<7;level++){
  const expected=new Set();
  for(const parent of record.subsets[level]){
   assert(parent.length===level&&parent.every((a,i)=>hs.has(a)&&(i===0||parent[i-1]<a)),"ordered parent");
   for(const a of H){if(level&&a<=parent[level-1])continue;extensions++;const child=[...parent,a];if(valid(child))expected.add(key(child));}
  }
  const saved=record.subsets[level+1],found=new Set(saved.map(key));
  assert(found.size===saved.length&&found.size===expected.size,"unique complete level");
  for(const k of expected)assert(found.has(k),"missing feasible projected subset");
 }
 const counts=record.subsets.map(a=>a.length);
 assert(same(counts,record.counts)&&same(counts,[1,42,524,2302,2903,996,0,0]),"level counts");
 return {original_projected_rows_before_dedup:rows.length,extension_tests:extensions,counts,method:"Every feasible subset is generated from its unique saved increasing prefix; direct original-row evaluation checks each extension."};
}
return {arithmetic,projection};
})()
