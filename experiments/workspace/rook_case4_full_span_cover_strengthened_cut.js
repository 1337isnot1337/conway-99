/* Original-coordinate proof of a strengthened H42 integer inequality.
No propagation, point scan, optimizer, or full coordinate-cover reconstruction. */
(() => {
"use strict";
const UPPER_ROWS=[368,411,431,590];
const SIX_ROWS_922=[[93,1],[243,1],[411,1],[589,1],[590,1],[591,1]];
const SIGNED_ROWS_600=[[60,-1],[93,2],[368,-2],[390,-1],[431,-2],[587,1],[589,2],[591,2],[593,1]];
function assert(x,m){if(!x)throw Error(m);}
function gram(I,terms){const c=Array(1214).fill(0);let b=0;for(const [id,w]of terms){assert(Number.isSafeInteger(id)&&id>=0&&id<630&&Number.isSafeInteger(w),"original Gram multiplier");const row=I.Gram_rows[id];b+=w*row[2];for(const a of row[3])c[a]+=w;}return {coefficients:c,rhs:b};}
function prove(I,theorem){
 const H=theorem.H,hs=new Set(H),zero=new Set(theorem.conditional_H_equals_five.prior_global_zero_columns);
 assert(H.length===42&&hs.size===42&&!hs.has(600)&&!hs.has(922)&&zero.has(783),"scope");
 const parity=gram(I,theorem.parity.original_row_ids.map(id=>[id,1]));
 assert(parity.rhs===81,"odd Gram RHS");
 const odd=parity.coefficients.map((c,a)=>[c,a]).filter(([c,a])=>(c&1)&&!zero.has(a)).map(([c,a])=>a);
 assert(JSON.stringify(odd)===JSON.stringify(H),"full original parity support");
 const parityZeros=parity.coefficients.map((c,a)=>[c,a]).filter(([c,a])=>(c&1)&&zero.has(a)).map(([c,a])=>a);
 const q=gram(I,UPPER_ROWS.map(id=>[id,1])),r=q.coefficients.map((c,a)=>c-(hs.has(a)?1:0));
 assert(q.rhs===5&&r.every(c=>c>=0),"upper five");
 const p922=gram(I,SIX_ROWS_922),s922=p922.coefficients.map((c,a)=>c-(hs.has(a)?1:0)-(a===922?3:0));
 assert(p922.rhs===7&&s922.every(c=>c>=0),"H+3x922<=7");
 const base600=gram(I,SIGNED_ROWS_600);
 assert(base600.rhs===3&&base600.coefficients[600]===4,"signed base");
 const s600=base600.coefficients.map((c,a)=>c+3*r[a]-(a===600?4:0));
 assert(s600.every((c,a)=>a===783?c===-1:c>=0),"sole negative residual is proved zero783");
 const combined=new Map(SIGNED_ROWS_600);
 for(const id of UPPER_ROWS)combined.set(id,(combined.get(id)||0)+3);
 const direct600=[...combined].filter(([id,v])=>v).sort((a,b)=>a[0]-b[0]),g600=gram(I,direct600);
 assert(g600.rhs===18&&g600.coefficients.every((c,a)=>c===3*(hs.has(a)?1:0)+(a===600?4:0)+s600[a]),"full1214 direct identity600");
 const cap=I.Gram_rows[617];assert(cap[0]===30&&cap[1]===32&&cap[2]===1&&cap[3].includes(600)&&cap[3].includes(922),"mutual quota-one");
 return {schema:"rook-case4-H42-short-strengthened-integer-cut-v1",H,needed_proved_zero_columns:[...new Set(parityZeros.concat([783]))].sort((a,b)=>a-b),parity:{original_Gram_rows:theorem.parity.original_row_ids,rhs:81,full1214_coefficients:parity.coefficients},upper_five:{original_Gram_rows:UPPER_ROWS,rhs:5,full1214_residual:r},bound922:{original_Gram_rows:SIX_ROWS_922,rhs:7,full1214_nonnegative_residual:s922,inequality:"sum_H x+3*x922<=7"},bound600:{signed_base_Gram_rows:SIGNED_ROWS_600,direct_Gram_rows:direct600,rhs:18,full1214_residual:s600,sole_negative_residual:[783,-1],inequality:"3*sum_H x+4*x600<=18+x783"},mutual_capacity:{original_Gram_row:617,core_pair:[30,32],rhs:1,residual_columns:cap[3].filter(a=>a!==600&&a!==922)},final_integer_inequality:{terms:H.map(a=>[a,1]).concat([[600,2],[922,2]]).sort((a,b)=>a[0]-b[0]),upper:5},logic:{possible_H_totals:[1,3,5],H5_bounds:{x600:"3/4",x922:"2/3"},if_H5:"nonnegative integrality gives x600=x922=0",if_H1_or_H3:"quota-one gives x600+x922<=1"},scope:"Necessary for original nonnegative integer Gram solutions with the seven listed proved zeros. No global zeros600/922, graph construction, or case4 exclusion."};
}
function literalControls(){
 let checked=0;
 for(const h of [1,3,5])for(const a of [0,1])for(const b of [0,1]){
  if(a+b>1||3*h+4*a>18||h+3*b>7)continue;
  assert(h+2*(a+b)<=5,"finite integer implication");checked++;
 }
 return {status:"PASS",feasible_integer_triples:checked,total_triples:12,optimizer_calls:0};
}
return {UPPER_ROWS,SIX_ROWS_922,SIGNED_ROWS_600,prove,literalControls};
})()
